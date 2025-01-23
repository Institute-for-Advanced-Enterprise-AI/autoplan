import pytest

from autoplan.chain import chain
from autoplan.tool import tool


@pytest.mark.asyncio
async def test_chain():
    @tool
    async def double(x: int) -> int:
        return x * 2

    @tool
    async def triple(x: int) -> int:
        return x * 3

    times_six = chain(double, triple)

    assert times_six.__name__ == "DoubleTriple"

    tool_instance = times_six(x=1)
    result = await tool_instance()
    assert result == 6


@pytest.mark.asyncio
async def test_chain_with_name():
    @tool
    async def double(x: int) -> int:
        return x * 2

    @tool
    async def triple(x: int) -> int:
        return x * 3

    times_six = chain(double, triple, name="times_six")

    # class name gets camel cased
    assert times_six.__name__ == "TimesSix"

    tool_instance = times_six(x=1)
    result = await tool_instance()
    assert result == 6


@pytest.mark.asyncio
async def test_chain_with_pass_through_parameters():
    @tool
    async def double_first(x: int, y: int) -> int:
        return x * 2

    @tool
    async def add(result: int, y: int) -> int:
        return result + y

    # y is passed through from tool1 to tool2
    chaind = chain(double_first, add)

    tool_instance = chaind(x=1, y=2)
    result = await tool_instance()
    assert result == 4


@pytest.mark.asyncio
async def test_chain_with_tool2_only_parameters():
    @tool
    async def double(x: int) -> int:
        return x * 2

    @tool
    async def add(result: int, y: int) -> int:
        return result + y

    chained = chain(double, add)

    # chained takes in "y" even though it's not in the tool1 parameters (only in tool2)
    tool_instance = chained(x=1, y=2)
    result = await tool_instance()
    assert result == 4
