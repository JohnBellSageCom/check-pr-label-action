#!/usr/bin/env python3

import os
import sys
import re
from github import Github


def get_env_var(env_var_name, echo_value=False):
    """Try to get the value from a environmental variable.

    If the values is 'None', then a ValueError exception will
    be thrown.

    Args:
        env_var_name (string): The name of the environmental variable.
        echo_value (bool): Print the resulting value

    Returns:
        string: the value from the environmental variable.
    """
    value = os.environ.get(env_var_name)

    if value == None:
        raise ValueError(
            f'The environmental variable {env_var_name} is empty!')

    if echo_value:
        print(f"{env_var_name} = {value}")

    return value


# Check if the number of input arguments is correct
if len(sys.argv) != 3:
    raise ValueError('Invalid number of arguments!')

# Get the GitHub token
token = sys.argv[1]

# Get the list of valid labels
valid_labels = sys.argv[2]
print(f'Valid labels are: {valid_labels}')

# Get needed values from the environmental variables
repo_name = get_env_var('GITHUB_REPOSITORY')
github_ref = get_env_var('GITHUB_REF')

# Create a repository object, using the GitHub token
repo = Github(token).get_repo(repo_name)

# Try to extract the pull request number from the GitHub reference.
try:
    pr_number = int(re.search('refs/pull/([0-9]+)/merge', github_ref).group(1))
    print(f'Pull request number: {pr_number}')
except AttributeError:
    raise ValueError(
        f'The Pull request number could not be extracted from the GITHUB_REF = {github_ref}')

# Create a pull request object
pr = repo.get_pull(pr_number)

# Get the pull request labels
pr_labels = pr.get_labels()

# This is a list of valid label found in the pull request
pr_valid_labels = []

# Check which of the label in the pull request, are in the
# list of valid labels
for label in pr_labels:
    if label.name in valid_labels:
        pr_valid_labels.append(label.name)

# Check if there were at least one valid label
# Note: In both cases we exit without an error code and let the check to succeed. This is because GitHub
# workflow will create different checks for different trigger conditions. So, adding a missing label won't
# clear the initial failed check during the PR creation, for example.
# Instead, we will create a pull request review, marked with 'REQUEST_CHANGES' when no valid label was found.
# This will prevent merging the pull request until a valid label is added, which will trigger this check again
# and will create a new pull request review, but in this case marked as 'APPROVE'

if len(pr_valid_labels):
    # If there were valid labels, dismiss the request for changes if present
    pr_reviews = pr.get_reviews()
    for pr_review in pr_reviews:
        if (pr_review.user.login == 'github-actions[bot]'
                or 'There are changes to production translations in this pull request' in pr_review.body) and pr_review.state == 'CHANGES_REQUESTED':
            print('Dismissing changes request')
            pr_review.dismiss(
                'Required label added to PR confirming intention to update production translations')


else:
    # If there were not valid labels, then create a pull request review, requesting changes
    print(
        f'Error! This pull request does not contain any of the valid labels: {valid_labels}')
    pr.create_review(body='There are changes to production translations in this pull request. '
                     f'Please add the following label: `{valid_labels}` to confirm that '
                     'you intend to make these changes.',
                     event='REQUEST_CHANGES')
