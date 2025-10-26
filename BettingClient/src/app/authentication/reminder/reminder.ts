import { Component, Input } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-reminder',
  imports: [FormsModule],
  templateUrl: './reminder.html'
})
export class Reminder {
  @Input() userData: UserData = {reminder: 0, summary: 0};
}
