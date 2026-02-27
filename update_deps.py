import json
import re
import urllib.request

with open("pyproject.toml", encoding="utf-8") as f:
    content = f.read()

deps_section = re.search(r"dependencies\s*=\s*\[(.*?)\]", content, re.DOTALL)
if deps_section:
    deps_text = deps_section.group(1)
    deps = deps_text.split("\n")
    new_deps = []
    for dep in deps:
        if not dep.strip():
            new_deps.append(dep)
            continue

        # Regex to extract package name and current constraint
        match = re.match(r"\s*\"([a-zA-Z0-9\-_]+)([>=<~].*)?\",?", dep)
        if match:
            pkg_name = match.group(1)
            # Find the latest version on PyPI
            try:
                url = f"https://pypi.org/pypi/{pkg_name}/json"
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode())
                    latest = data["info"]["version"]

                # Retain the exact operator if it was pinned strictly
                # or use >= by default
                operator = "==" if "==" in dep else ">="

                new_deps.append(f'    "{pkg_name}{operator}{latest}",')
                print(f"Updated {pkg_name} to {latest}")
            except Exception as e:
                print(f"Failed to fetch {pkg_name}: {e}")
                new_deps.append(dep)
        else:
            new_deps.append(dep)

    new_content = content[: deps_section.start(1)] + "\n".join(new_deps) + "\n" + content[deps_section.end(1) :]
    with open("pyproject.toml", "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Done writing pyproject.toml")
else:
    print("Could not find dependencies section.")
