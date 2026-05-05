# Apply Pillow decompression-bomb cap at process start. Importing the module
# is the side-effect; callers in moderation/uploads/tools all rely on it.
from . import imaging  # noqa: F401
