import sys

# print sys.path
# print(sys.path)


# import sys  # pylint: disable=wrong-import-order
# import pathlib  # pylint: disable=wrong-import-order
# # Add parent directory to path in order to import config.
# # This is necessary because the GitHub Actions workflow runs the script
# # from the infrastructure/publish_server directory, and is unable to
# # import from the parent directory (infrastructure).
# current_dir = pathlib.Path(__file__).resolve().parent
# parent_dir = current_dir.parent
# sys.path.append(str(parent_dir))
# print(str(parent_dir))

import config  # pylint: disable=wrong-import-order,wrong-import-position

from infrastructure import config
