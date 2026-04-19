export type TreeNode = {
  name: string;
  path: string;
  isFile: boolean;
  children: TreeNode[];
};

/**
 * Converts a flat list of file paths into a nested tree structure.
 * Paths use "/" as separator. Folders are created as needed; leaf nodes are files.
 */
export function buildTree(files: string[]): TreeNode[] {
  const root: TreeNode = { name: '', path: '', isFile: false, children: [] };

  for (const file of files) {
    const parts = file.split('/').filter(Boolean);
    if (parts.length === 0) continue;

    let current = root;
    for (let i = 0; i < parts.length - 1; i++) {
      const part = parts[i];
      let child = current.children.find((c) => c.name === part && !c.isFile);
      if (!child) {
        child = { name: part, path: '', isFile: false, children: [] };
        current.children.push(child);
      }
      current = child;
    }
    const fileName = parts[parts.length - 1];
    if (!current.children.some((c) => c.name === fileName && c.path === file)) {
      current.children.push({ name: fileName, path: file, isFile: true, children: [] });
    }
  }

  function sortNode(node: TreeNode): void {
    node.children.sort((a, b) => {
      if (a.isFile !== b.isFile) return a.isFile ? 1 : -1;
      return a.name.localeCompare(b.name, undefined, { sensitivity: 'base' });
    });
    node.children.forEach(sortNode);
  }
  sortNode(root);
  return root.children;
}
