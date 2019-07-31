def current_repo_list():
    repos = []
    with open('repos.txt', 'r') as f:
        repos = f.read().splitlines()
    return repos
