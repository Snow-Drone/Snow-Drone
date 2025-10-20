#!/bin/bash
: '
@# Description:
This script retrieves the global git configuration for username and email.
If the values are not set, it prompts the user to input them and set them globally.

@# **Please Note**: When starting on this project, ensure you unset any existing global git config values
for username and email to avoid conflicts. Please uncomment the relevant lines below. Set your own git config
values before running any git commands.

@# Usage:
Run the script in a bash environment. Uncomment relevant lines to set or unset git config values.

@# Note: Dont be stupid and commit your actual username and email to a public repository. Always double-check before committing.
'

username=$(git config user.name)
email=$(git config user.email)

echo "$username"
echo "$email"

## The following lines can be uncommented to unset existing global git config values
# git config --global unset user.name
# git config --global unset user.email

## Set git username and email if not already set. Interactively promts the user for input.
## uncomment to use.
# if [ -z "$username" ]; then
#     echo "Git username is not set. Please enter your Git username:"
#     read username
#     git config --global user.name "$username"
# fi
# if [ -z "$email" ]; then
#     echo "Git email is not set. Please enter your Git email:"
#     read email
#     git config --global user.email "$email"
# fi