
from autoplan import Dependency

[% for input in config.inputs %]
[[input]]= Dependency()
[% endfor %]
