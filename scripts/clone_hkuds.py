import os
import requests
import subprocess

def get_hkuds_repos(token=None):
    """获取 HKUDS 组织下所有仓库的 clone_url"""
    repos = []
    page = 1
    per_page = 100
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    
    while True:
        url = f"https://api.github.com/orgs/HKUDS/repos?per_page={per_page}&page={page}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"❌ 获取第 {page} 页失败：{response.text}")
            break
        
        page_repos = response.json()
        if not page_repos:
            break  # 没有更多仓库
        
        for repo in page_repos:
            repos.append(repo["clone_url"])
        print(f"✅ 获取第 {page} 页，共 {len(page_repos)} 个仓库")
        page += 1
    return repos

def clone_repos(repo_urls, target_dir="hkuds_repos"):
    """批量克隆仓库"""
    os.makedirs(target_dir, exist_ok=True)
    os.chdir(target_dir)
    
    for repo_url in repo_urls:
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        if os.path.exists(repo_name):
            print(f"✅ 仓库 {repo_name} 已存在，跳过")
            continue
        
        print(f"🔄 正在克隆 {repo_url}...")
        result = subprocess.run(
            ["git", "clone", repo_url],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ 克隆 {repo_name} 成功")
        else:
            print(f"❌ 克隆 {repo_name} 失败：{result.stderr}")

if __name__ == "__main__":
    # 从环境变量读取 Token（可选，公共仓库无需）
    import os
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")  # 设置: export GITHUB_TOKEN=ghp_xxxx
    repos = get_hkuds_repos(GITHUB_TOKEN)
    print(f"\n📊 共获取 {len(repos)} 个仓库")
    if repos:
        clone_repos(repos, target_dir="./")
    print("\n🎉 批量克隆完成！")
