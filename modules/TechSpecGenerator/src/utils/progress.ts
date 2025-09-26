/**
 * Simple progress tracking utility
 */

import { console } from './console';

export interface Task {
  id: string;
  description: string;
  completed: boolean;
}

export class Progress {
  private tasks: Map<string, Task> = new Map();

  addTask(description: string): string {
    const id = `task_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const task: Task = {
      id,
      description,
      completed: false
    };
    
    this.tasks.set(id, task);
    console.print(`[cyan]⏳[/cyan] ${description}`);
    return id;
  }

  updateTask(id: string, description: string): void {
    const task = this.tasks.get(id);
    if (task) {
      task.description = description;
      if (!task.completed) {
        console.print(`[cyan]⏳[/cyan] ${description}`);
      }
    }
  }

  completeTask(id: string, finalDescription?: string): void {
    const task = this.tasks.get(id);
    if (task) {
      task.completed = true;
      const desc = finalDescription || task.description;
      console.print(`[green]✓[/green] ${desc}`);
    }
  }

  failTask(id: string, errorDescription: string): void {
    const task = this.tasks.get(id);
    if (task) {
      task.completed = true;
      console.print(`[red]✗[/red] ${errorDescription}`);
    }
  }

  async withProgress<T>(
    description: string,
    asyncFunction: () => Promise<T>
  ): Promise<T> {
    const taskId = this.addTask(description);
    try {
      const result = await asyncFunction();
      this.completeTask(taskId);
      return result;
    } catch (error) {
      this.failTask(taskId, `${description} - Failed: ${error}`);
      throw error;
    }
  }
}