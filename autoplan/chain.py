from typing import Any, Optional, Union

from pydantic import BaseModel

from autoplan.tool import Tool, tool


def chain(
    tool1: type[Tool],
    tool2: type[Tool],
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> type[Tool]:
    """
    Chains two tools together by constructing a new function that calls the first tool with the given parameters,
    then passes the result to the second tool.
    """

    # we need to figure out how the tool2 parameters relate to the tool1 parameters
    tool2_parameters = {
        k: v.annotation for k, v in tool2.model_fields.items() if k != "type"
    }

    # tool2 parameters that have the same name as tool1 parameters
    tool2_parameters_included_in_tool1 = {
        k: v
        for k, v in tool1.model_fields.items()
        if k in tool2_parameters and k != "type"
    }

    tool2_parameters_not_included_in_tool1 = {
        k: v
        for k, v in tool2_parameters.items()
        if k not in tool1.model_fields and k != "type"
    }

    # if there are parameters in tool2 that are not in tool1, we assume the first parameter represents the result of the first tool
    if tool2_parameters_not_included_in_tool1:
        result_key = next(iter(tool2_parameters_not_included_in_tool1))
    # otherwise, we assume the name is reused
    else:
        result_key = next(iter(tool2_parameters_included_in_tool1))

    tool2_parameters_provided_by_tool_1 = [
        key for key in tool2_parameters if key != result_key
    ]

    parameters_from_tool_1 = {
        k: v.annotation for k, v in tool1.model_fields.items() if k != "type"
    }

    parameters_from_tool_2 = {
        k: v.annotation
        for k, v in tool2.model_fields.items()
        if k != "type"
        and k in tool2_parameters_not_included_in_tool1
        and k != result_key
    }
    parameters = {
        k: v
        for k, v in {**parameters_from_tool_1, **parameters_from_tool_2}.items()
        if v is not None
    }

    fn_name = name or tool1.__name__ + "_" + tool2.__name__

    async def core(**kwargs):
        # construct an instance of the first tool
        tool1_instance = tool1(**kwargs)

        # call the first tool
        tool1_result = await tool1_instance()

        tool2_kwargs: dict[str, Any] = {result_key: tool1_result} | {
            k: v for k, v in kwargs.items() if k in tool2_parameters_provided_by_tool_1
        }

        # construct an instance of the second tool
        tool2_instance = tool2(**tool2_kwargs)

        # call the second tool
        return await tool2_instance()

    # We need the function to have explicit parameters that match the tool1 parameters
    # To do this, we use exec to evaluate code that we templated with the tool1 parameters

    # See: https://stackoverflow.com/questions/26987418/programmatically-create-function-specification

    # Example:
    # async def Double_Triple(x: int):
    #     return await core(x=x)

    code = f"""
async def {fn_name}({', '.join(f'{k}: {v.__name__ if not hasattr(v, "__args__") else v.__args__[0].__name__}' for k, v in parameters.items())}):
    return await core({', '.join(f'{k}={k}' for k in parameters)})
    """

    env = {"core": core}

    namespace = {"Union": Union, "BaseModel": BaseModel}
    exec(code, env, namespace)
    f = tool(namespace[fn_name])
    f.__doc__ = description
    return f
