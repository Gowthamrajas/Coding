import * as vscode from "vscode";
import { formatMatchSummary, maskText, scanText } from "./detector";
import { SensitiveMatch } from "./types";

let statusBarItem: vscode.StatusBarItem;
let latestMatches: SensitiveMatch[] = [];

function getCustomPatterns(): Array<{ label: string; pattern: string; ignoreCase?: boolean }> {
  return vscode.workspace.getConfiguration("promptGuard").get("customPatterns", []);
}

function isEnabled(): boolean {
  return vscode.workspace.getConfiguration("promptGuard").get("enabled", true);
}

function updateStatusBar(matches: SensitiveMatch[]): void {
  latestMatches = matches;
  if (!vscode.workspace.getConfiguration("promptGuard").get("warnInStatusBar", true)) {
    statusBarItem.hide();
    return;
  }

  statusBarItem.text = formatMatchSummary(matches);
  statusBarItem.tooltip = matches.length
    ? matches.map((match) => `${match.label}: ${match.value}`).join("\n")
    : "No sensitive data detected in the latest scan";
  statusBarItem.backgroundColor = matches.length
    ? new vscode.ThemeColor("statusBarItem.warningBackground")
    : undefined;
  statusBarItem.show();
}

async function scanAndReport(text: string, source: string): Promise<SensitiveMatch[]> {
  const matches = scanText(text, getCustomPatterns());
  updateStatusBar(matches);

  if (matches.length === 0) {
    void vscode.window.showInformationMessage(`${source}: no sensitive data detected.`);
    return matches;
  }

  const detail = matches
    .map((match) => `${match.label}: "${match.value}" -> ${match.placeholder}`)
    .join("\n");
  const action = await vscode.window.showWarningMessage(
    `${source}: detected ${matches.length} sensitive segment(s).`,
    { modal: false, detail },
    "Sanitize",
    "Show Panel"
  );

  if (action === "Sanitize") {
    await vscode.commands.executeCommand("promptGuard.showPanel");
  } else if (action === "Show Panel") {
    await vscode.commands.executeCommand("promptGuard.showPanel");
  }

  return matches;
}

function getActiveSelectionOrDocument(): { text: string; editor: vscode.TextEditor } | undefined {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    void vscode.window.showWarningMessage("Prompt Guard: open a file or select text first.");
    return undefined;
  }

  const text = editor.selection.isEmpty
    ? editor.document.getText()
    : editor.document.getText(editor.selection);
  return { text, editor };
}

export function activate(context: vscode.ExtensionContext): void {
  statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
  statusBarItem.command = "promptGuard.showPanel";
  context.subscriptions.push(statusBarItem);

  context.subscriptions.push(
    vscode.commands.registerCommand("promptGuard.scanSelection", async () => {
      if (!isEnabled()) {
        return;
      }
      const payload = getActiveSelectionOrDocument();
      if (!payload) {
        return;
      }
      await scanAndReport(payload.text, "Scan");
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("promptGuard.scanDocument", async () => {
      if (!isEnabled()) {
        return;
      }
      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        void vscode.window.showWarningMessage("Prompt Guard: open a document first.");
        return;
      }
      await scanAndReport(editor.document.getText(), "Document scan");
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("promptGuard.sanitizeSelection", async () => {
      if (!isEnabled()) {
        return;
      }
      const payload = getActiveSelectionOrDocument();
      if (!payload) {
        return;
      }

      const matches = scanText(payload.text, getCustomPatterns());
      if (matches.length === 0) {
        void vscode.window.showInformationMessage("Prompt Guard: nothing to sanitize.");
        return;
      }

      const sanitized = maskText(payload.text, matches);
      const targetRange = payload.editor.selection.isEmpty
        ? new vscode.Range(payload.editor.document.positionAt(0), payload.editor.document.positionAt(payload.text.length))
        : payload.editor.selection;

      await payload.editor.edit((editBuilder) => {
        editBuilder.replace(targetRange, sanitized);
      });
      updateStatusBar(matches);
      void vscode.window.showInformationMessage(
        `Prompt Guard: replaced ${matches.length} sensitive segment(s) with placeholders.`
      );
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("promptGuard.sanitizeAndCopy", async () => {
      if (!isEnabled()) {
        return;
      }
      const payload = getActiveSelectionOrDocument();
      if (!payload) {
        return;
      }

      const matches = scanText(payload.text, getCustomPatterns());
      const sanitized = maskText(payload.text, matches);
      await vscode.env.clipboard.writeText(sanitized);
      updateStatusBar(matches);

      if (matches.length === 0) {
        void vscode.window.showInformationMessage("Prompt Guard: copied text (no sensitive data found).");
        return;
      }

      void vscode.window.showInformationMessage(
        `Prompt Guard: copied sanitized text with ${matches.length} replacement(s). Paste this into chat.`
      );
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("promptGuard.showPanel", async () => {
      if (latestMatches.length === 0) {
        void vscode.window.showInformationMessage("Prompt Guard: no findings yet. Run a scan first.");
        return;
      }

      const items = latestMatches.map((match) => ({
        label: match.label,
        description: match.placeholder,
        detail: match.value,
      }));
      await vscode.window.showQuickPick(items, {
        title: "Prompt Guard Findings",
        placeHolder: "Review detected sensitive segments",
      });
    })
  );

  context.subscriptions.push(
    vscode.workspace.onDidSaveTextDocument(async (document) => {
      if (!isEnabled() || !vscode.workspace.getConfiguration("promptGuard").get("scanOnSave", false)) {
        return;
      }
      const editor = vscode.window.activeTextEditor;
      if (!editor || editor.document !== document) {
        return;
      }
      const matches = scanText(document.getText(), getCustomPatterns());
      updateStatusBar(matches);
    })
  );

  updateStatusBar([]);
}

export function deactivate(): void {
  statusBarItem?.dispose();
}
