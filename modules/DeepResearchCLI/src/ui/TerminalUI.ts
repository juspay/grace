import * as blessed from 'blessed';
import { LogEntry, UserAction } from '../types';
import chalk from 'chalk';

// Enhanced UI themes inspired by Claude Code
const themes = {
  claude: {
    primary: 'red' as any,
    secondary: 'cyan' as any,
    accent: 'blue' as any,
    success: 'green' as any,
    warning: 'yellow' as any,
    error: 'red' as any,
    info: 'blue' as any,
    text: 'white' as any,
    border: 'grey' as any,
    background: 'black' as any
  },
  modern: {
    primary: 'magenta' as any,
    secondary: 'cyan' as any,
    accent: 'blue' as any,
    success: 'green' as any,
    warning: 'yellow' as any,
    error: 'red' as any,
    info: 'blue' as any,
    text: 'white' as any,
    border: 'grey' as any,
    background: 'black' as any
  }
};

const currentTheme = themes.claude;

export interface TerminalUIOptions {
  title: string;
  onUserAction: (action: UserAction) => void;
}

export class TerminalUI {
  private screen: any;
  private logBox: any;
  private statusBox: any;
  private inputBox: any;
  private progressBar: any;
  private optionsBox: any;
  private headerBox: any;
  private sidePanel: any;
  private onUserAction: (action: UserAction) => void;
  private logEntries: LogEntry[] = [];
  private currentExpandedItems: Set<number> = new Set();
  private currentSelectedIndex: number = -1;
  private animationFrame: NodeJS.Timeout | null = null;
  private components: Map<string, any> = new Map();
  private isAdvancedMode: boolean = false;

  constructor(options: TerminalUIOptions) {
    this.onUserAction = options.onUserAction;
    this.screen = blessed.screen({
      smartCSR: true,
      title: options.title,
      cursor: {
        artificial: true,
        shape: 'line',
        blink: true,
        color: 'cyan'
      },
      autoPadding: false,
      warnings: false,
      fullUnicode: true,
      sendFocus: false,     // Prevent focus events from interfering
      useBCE: false,        // Disable background color erase to prevent issues
      resizeTimeout: 300,   // Add resize timeout to prevent flickering
      forceUnicode: false,  // Disable forced unicode to prevent encoding issues
      dockBorders: false,   // Disable dock borders to prevent interference
      ignoreLocked: ['C-c'] // Allow Ctrl+C to work properly
    });

    this.setupLayout();
    this.setupKeyBindings();
    this.startAnimations();
  }

  private createHeaderContent(): string {
    const timestamp = new Date().toLocaleTimeString();
    return `{center}{red-fg}⚡ Grace Deep Research CLI{/red-fg} {cyan-fg}v2.0{/cyan-fg} {|} {blue-fg}${timestamp}{/blue-fg}{/center}`;
  }

  private createStatusContent(status: string, type: 'info' | 'success' | 'warning' | 'error'): string {
    const icons = {
      info: '📊',
      success: '✅',
      warning: '⚠️',
      error: '❌'
    };
    const colorMap = {
      info: 'blue-fg',
      success: 'green-fg',
      warning: 'yellow-fg',
      error: 'red-fg'
    };
    return `{left}${icons[type]} {${colorMap[type]}}${status}{/${colorMap[type]}}{/left}`;
  }

  private createSidePanelContent(): string {
    return `{center}{blue-fg}💡 Smart Mode{/blue-fg}\n{center}{cyan-fg}[F4] Toggle{/cyan-fg}{/center}`;
  }

  private startAnimations(): void {
    this.animationFrame = setInterval(() => {
      if (this.headerBox) {
        this.headerBox.setContent(this.createHeaderContent());
        this.screen.render();
      }
    }, 1000);
  }

  private setupLayout() {
    // Enhanced Header with Claude Code styling
    this.headerBox = blessed.box({
      parent: this.screen,
      top: 0,
      left: 0,
      width: '100%',
      height: 4,
      content: this.createHeaderContent(),
      tags: true,
      border: {
        type: 'line',
        fg: currentTheme.primary
      },
      style: {
        fg: currentTheme.text,
        border: {
          fg: currentTheme.primary
        }
      }
    });
    this.components.set('header', this.headerBox);

    // Enhanced Status Box
    this.statusBox = blessed.box({
      parent: this.screen,
      top: 4,
      left: 0,
      width: '70%',
      height: 3,
      content: this.createStatusContent('Ready', 'info'),
      tags: true,
      border: {
        type: 'line',
        fg: currentTheme.info
      },
      style: {
        fg: currentTheme.text,
        border: {
          fg: currentTheme.info
        }
      }
    });
    this.components.set('status', this.statusBox);

    // Side Panel for metrics and controls
    this.sidePanel = blessed.box({
      parent: this.screen,
      top: 4,
      right: 0,
      width: '30%',
      height: 3,
      content: this.createSidePanelContent(),
      tags: true,
      border: {
        type: 'line',
        fg: currentTheme.secondary
      },
      style: {
        fg: currentTheme.text,
        border: {
          fg: currentTheme.secondary
        }
      }
    });
    this.components.set('sidePanel', this.sidePanel);

    // Enhanced Progress Bar
    this.progressBar = blessed.progressbar({
      parent: this.screen,
      top: 7,
      left: 2,
      width: -4,
      height: 1,
      orientation: 'horizontal',
      style: {
        bar: {
          bg: currentTheme.accent
        }
      },
      ch: '━',
      filled: 0
    });
    this.components.set('progress', this.progressBar);

    // Enhanced Main Log Area
    this.logBox = blessed.log({
      parent: this.screen,
      top: 9,
      left: 0,
      width: '100%',
      height: -12,
      tags: true,
      keys: true,
      vi: true,
      mouse: false, // Disable mouse to prevent interference
      scrollback: 1000,
      scrollbar: {
        ch: '█',
        track: {
          bg: currentTheme.border
        },
        style: {
          inverse: false,
          fg: currentTheme.accent
        }
      },
      border: {
        type: 'line',
        fg: currentTheme.border
      },
      style: {
        fg: currentTheme.text,
        border: {
          fg: currentTheme.border
        },
        selected: {
          bg: currentTheme.accent,
          fg: currentTheme.text
        }
      }
    });
    this.components.set('logBox', this.logBox);

    // Enhanced Options Box
    this.optionsBox = blessed.box({
      parent: this.screen,
      bottom: 4,
      left: 0,
      width: '100%',
      height: 3,
      content: '{center}⌨️ Controls: [F1] Skip [F2] Cancel [F3] History [F4] Smart Mode [Space] Expand [↑↓] Navigate{/center}',
      tags: true,
      border: {
        type: 'line',
        fg: currentTheme.warning
      },
      style: {
        fg: currentTheme.text,
        border: {
          fg: currentTheme.warning
        }
      }
    });
    this.components.set('options', this.optionsBox);

    // Enhanced Input Box
    this.inputBox = blessed.textbox({
      parent: this.screen,
      bottom: 0,
      left: 0,
      width: '100%',
      height: 3,
      keys: true,
      mouse: false, // Disable mouse to prevent interference
      inputOnFocus: true,
      secretInput: false,
      censor: false,
      content: '',
      wrap: false,
      scrollable: false,
      alwaysScroll: false,
      input: true,
      border: {
        type: 'line',
        fg: currentTheme.primary
      },
      style: {
        fg: currentTheme.text,
        focus: {
          border: {
            fg: currentTheme.accent
          }
        }
      },
      label: ' 💬 Input '
    });
    this.components.set('input', this.inputBox);

    this.screen.render();
  }

  private setupKeyBindings() {
    // Disable mouse support at screen level to prevent interference
    this.screen.enableMouse = () => {}; // Disable mouse support

    // Remove any existing mouse event listeners
    this.screen.removeAllListeners('mouse');

    // More specific key bindings to avoid accidental exits
    this.screen.key(['C-c'], () => {
      // Confirmation before exit
      this.showConfirmExit();
    });

    this.screen.key(['f1'], () => {
      this.onUserAction({ type: 'skip' });
    });

    this.screen.key(['f2'], () => {
      this.showConfirmCancel();
    });

    this.screen.key(['f3'], () => {
      this.onUserAction({ type: 'skip', data: { showHistory: true } });
    });

    this.screen.key(['f4'], () => {
      this.toggleSmartMode();
    });

    this.screen.key(['space'], () => {
      this.toggleExpanded();
    });

    // Enhanced keyboard navigation
    this.screen.key(['up', 'k'], () => {
      this.navigateLog(-1);
    });

    this.screen.key(['down', 'j'], () => {
      this.navigateLog(1);
    });

    // Input box key bindings - use submit event only to prevent double triggering
    this.inputBox.on('submit', (data: string) => {
      const input = data?.trim() || this.inputBox.getValue().trim();
      if (input) {
        this.onUserAction({ type: 'input', data: { message: input } });
        this.clearInput();
        this.logBox.focus();
        this.screen.render();
      }
    });

    // Handle input clearing on escape
    this.inputBox.key('escape', () => {
      this.clearInput();
      this.logBox.focus();
      this.screen.render();
    });

    // Focus management
    this.logBox.key('tab', () => {
      this.inputBox.focus();
    });

    this.inputBox.key('tab', () => {
      this.logBox.focus();
    });

    // Set initial focus
    this.logBox.focus();
  }

  public updateStatus(status: string, type: 'info' | 'success' | 'warning' | 'error' = 'info') {
    this.statusBox.setContent(this.createStatusContent(status, type));

    const themeColors = {
      info: currentTheme.info,
      success: currentTheme.success,
      warning: currentTheme.warning,
      error: currentTheme.error
    };

    this.statusBox.style.border.fg = themeColors[type];
    this.screen.render();
  }

  private toggleSmartMode(): void {
    this.isAdvancedMode = !this.isAdvancedMode;
    const modeText = this.isAdvancedMode ? 'Advanced Mode' : 'Smart Mode';
    this.sidePanel.setContent(`{center}{blue-fg}💡 ${modeText}{/blue-fg}\n{center}{cyan-fg}[F4] Toggle{/cyan-fg}{/center}`);
    this.updateStatus(`Switched to ${modeText}`, 'info');
    this.screen.render();
  }

  public updateProgress(percentage: number, text?: string) {
    this.progressBar.setProgress(percentage);
    if (text) {
      this.progressBar.setContent(text);
    }
    this.screen.render();
  }

  public addLogEntry(entry: LogEntry) {
    this.logEntries.push(entry);
    this.renderLogEntries();
  }

  public addSearchStep(query: string, depth: number = 0) {
    const entry: LogEntry = {
      timestamp: Date.now(),
      type: 'search',
      message: `Search → "${query}"`,
      depth,
      expandable: true,
      expanded: false,
      children: []
    };
    this.addLogEntry(entry);
  }

  public addPageFetchStep(url: string, depth: number, parent?: number) {
    const entry: LogEntry = {
      timestamp: Date.now(),
      type: 'fetch',
      message: `├── Fetching: ${this.truncateUrl(url)}`,
      url,
      depth,
      expandable: false
    };

    if (parent !== undefined && this.logEntries[parent]) {
      this.logEntries[parent].children = this.logEntries[parent].children || [];
      this.logEntries[parent].children!.push(entry);
    } else {
      this.addLogEntry(entry);
    }
  }

  public addProcessingStep(url: string, info: string, depth: number) {
    const entry: LogEntry = {
      timestamp: Date.now(),
      type: 'process',
      message: `    ├── Processing: ${info}`,
      url,
      depth
    };
    this.addLogEntry(entry);
  }

  public addAnalysisStep(message: string, depth: number) {
    const entry: LogEntry = {
      timestamp: Date.now(),
      type: 'analysis',
      message: `    └── ${message}`,
      depth
    };
    this.addLogEntry(entry);
  }

  public addFoundLinks(count: number, depth: number) {
    const entry: LogEntry = {
      timestamp: Date.now(),
      type: 'info',
      message: `      └── Found ${count} relevant links for depth ${depth + 1}`,
      depth,
      expandable: count > 0,
      expanded: false
    };
    this.addLogEntry(entry);
  }

  public addError(message: string, url?: string) {
    const entry: LogEntry = {
      timestamp: Date.now(),
      type: 'error',
      message: `❌ Error: ${message}`,
      url
    };
    this.addLogEntry(entry);
  }

  private renderLogEntries() {
    this.logBox.setContent('');

    for (let i = 0; i < this.logEntries.length; i++) {
      const entry = this.logEntries[i];
      this.renderLogEntry(entry, i);
    }

    this.logBox.setScrollPerc(100);
    this.screen.render();
  }

  private renderLogEntry(entry: LogEntry, index: number, indentLevel: number = 0) {
    const indent = '  '.repeat(indentLevel);
    const timestamp = new Date(entry.timestamp).toLocaleTimeString();

    let icon = '';
    let color: 'cyan' | 'yellow' | 'blue' | 'magenta' | 'red' | 'green' | 'white' = 'white';

    switch (entry.type) {
      case 'search':
        icon = '🔍';
        color = 'cyan';
        break;
      case 'fetch':
        icon = '📥';
        color = 'yellow';
        break;
      case 'process':
        icon = '⚙️';
        color = 'blue';
        break;
      case 'analysis':
        icon = '🧠';
        color = 'magenta';
        break;
      case 'error':
        icon = '❌';
        color = 'red';
        break;
      case 'info':
        icon = '📋';
        color = 'green';
        break;
    }

    let expandIcon = '';
    if (entry.expandable) {
      expandIcon = entry.expanded ? '[-] ' : '[+] ';
    }

    const logLine = `${indent}${expandIcon}${icon} ${chalk[color](entry.message)} ${chalk.gray(`[${timestamp}]`)}`;
    this.logBox.log(logLine);

    // Render children if expanded
    if (entry.expanded && entry.children) {
      entry.children.forEach(child => {
        this.renderLogEntry(child, -1, indentLevel + 1);
      });
    }
  }

  private toggleExpanded() {
    // Find the currently selected log entry and toggle its expanded state
    const selectedIndex = this.logEntries.length - 1; // For simplicity, toggle the last expandable item

    for (let i = this.logEntries.length - 1; i >= 0; i--) {
      if (this.logEntries[i].expandable) {
        this.logEntries[i].expanded = !this.logEntries[i].expanded;
        this.renderLogEntries();
        break;
      }
    }
  }

  private truncateUrl(url: string, maxLength: number = 60): string {
    if (url.length <= maxLength) return url;
    return url.substring(0, maxLength - 3) + '...';
  }

  private navigateLog(direction: number): void {
    const maxIndex = this.logEntries.length - 1;
    this.currentSelectedIndex = Math.max(0, Math.min(maxIndex, this.currentSelectedIndex + direction));
    this.renderLogEntries();
  }

  private clearInput(): void {
    if (this.inputBox) {
      this.inputBox.clearValue();
      this.inputBox.setValue('');
      this.inputBox.value = '';
      this.inputBox.setContent('');
    }
  }

  public destroy() {
    if (this.animationFrame) {
      clearInterval(this.animationFrame);
      this.animationFrame = null;
    }

    // Clean up all event listeners to prevent memory leaks and double events
    this.screen.removeAllListeners();
    if (this.inputBox) {
      this.inputBox.removeAllListeners();
    }
    if (this.logBox) {
      this.logBox.removeAllListeners();
    }

    this.components.clear();
    this.screen.destroy();
  }

  public async prompt(message: string): Promise<string> {
    return new Promise((resolve) => {
      this.clearInput();
      this.statusBox.setContent(`💬 ${message}`);
      this.inputBox.focus();
      this.screen.render();

      const onSubmit = () => {
        const input = this.inputBox.getValue().trim();
        this.inputBox.removeListener('submit', onSubmit);
        this.logBox.focus();
        resolve(input);
      };

      this.inputBox.on('submit', onSubmit);
    });
  }

  public showHistory(sessions: any[]) {
    const historyContent = sessions.map((session, index) => {
      const duration = session.endTime ?
        Math.round((session.endTime - session.startTime) / 1000) :
        'Running';
      return `${index + 1}. ${session.query} - ${session.status} (${duration}s)`;
    }).join('\n');

    const historyBox = blessed.box({
      parent: this.screen,
      top: 'center',
      left: 'center',
      width: '80%' as any,
      height: '60%' as any,
      content: `Research History:\n\n${historyContent}`,
      tags: true,
      border: {
        type: 'line',
        fg: currentTheme.secondary
      },
      style: {
        fg: currentTheme.text,
        border: {
          fg: currentTheme.secondary
        }
      }
    });

    historyBox.key(['escape', 'enter'], () => {
      this.screen.remove(historyBox);
      this.screen.render();
    });

    historyBox.focus();
    this.screen.render();
  }

  private showConfirmExit(): void {
    const confirmBox = blessed.box({
      parent: this.screen,
      top: 'center',
      left: 'center',
      width: 50,
      height: 8,
      content: '{center}Are you sure you want to exit?\n\n[Y] Yes    [N] No{/center}',
      tags: true,
      border: {
        type: 'line',
        fg: currentTheme.error
      },
      style: {
        fg: currentTheme.text,
        border: {
          fg: currentTheme.error
        }
      }
    });

    confirmBox.key(['y', 'Y'], () => {
      this.onUserAction({ type: 'cancel' });
      process.exit(0);
    });

    confirmBox.key(['n', 'N', 'escape'], () => {
      this.screen.remove(confirmBox);
      this.screen.render();
    });

    confirmBox.focus();
    this.screen.render();
  }

  private showConfirmCancel(): void {
    const confirmBox = blessed.box({
      parent: this.screen,
      top: 'center',
      left: 'center',
      width: 50,
      height: 8,
      content: '{center}Cancel current research?\n\n[Y] Yes    [N] No{/center}',
      tags: true,
      border: {
        type: 'line',
        fg: currentTheme.warning
      },
      style: {
        fg: currentTheme.text,
        border: {
          fg: currentTheme.warning
        }
      }
    });

    confirmBox.key(['y', 'Y'], () => {
      this.screen.remove(confirmBox);
      this.onUserAction({ type: 'cancel' });
      this.screen.render();
    });

    confirmBox.key(['n', 'N', 'escape'], () => {
      this.screen.remove(confirmBox);
      this.screen.render();
    });

    confirmBox.focus();
    this.screen.render();
  }

  public showAIError(error: string, configHelp: string): void {
    const errorBox = blessed.box({
      parent: this.screen,
      top: 'center',
      left: 'center',
      width: '80%' as any,
      height: '60%' as any,
      content: `{center}{red-fg}🤖 AI Configuration Error{/red-fg}{/center}\n\n{red-fg}Error:{/red-fg} ${error}\n\n{yellow-fg}Configuration Help:{/yellow-fg}\n${configHelp}\n\n{green-fg}Press [Enter] to continue or [Ctrl+C] to exit{/green-fg}`,
      tags: true,
      border: {
        type: 'line',
        fg: currentTheme.error
      },
      style: {
        fg: currentTheme.text,
        border: {
          fg: currentTheme.error
        }
      },
      scrollable: true,
      alwaysScroll: true
    });

    errorBox.key(['enter', 'escape'], () => {
      this.screen.remove(errorBox);
      this.screen.render();
    });

    errorBox.focus();
    this.screen.render();
  }
}