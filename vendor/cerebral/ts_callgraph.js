// A small helper to emit TS/JS call edges using ts-morph
// Output: one JSON object per line { caller_id, caller_name, caller_path, callee_name }

const { Project, SyntaxKind } = require('ts-morph');

function main() {
  const filePath = process.argv[2];
  const project = new Project({
    tsConfigFilePath: undefined,
    useInMemoryFileSystem: false,
    skipAddingFilesFromTsConfig: true,
  });
  const source = project.addSourceFileAtPath(filePath);
  const functions = source.getFunctions();
  for (const fn of functions) {
    const name = fn.getName() || '<anonymous>';
    const start = fn.getStartLineNumber();
    const end = fn.getEndLineNumber();
    const callerId = `${filePath}:${name}:${start}-${end}`;
    const calls = fn.getDescendantsOfKind(SyntaxKind.CallExpression);
    for (const call of calls) {
      const expr = call.getExpression();
      let callee = '';
      if (expr.getKindName() === 'Identifier') {
        callee = expr.getText();
      } else if (expr.getKindName() === 'PropertyAccessExpression') {
        callee = expr.getName();
      } else {
        callee = expr.getText().slice(0, 64);
      }
      const rec = {
        caller_id: callerId,
        caller_name: name,
        caller_path: filePath,
        callee_name: callee,
      };
      process.stdout.write(JSON.stringify(rec) + '\n');
    }
  }
}

main();
