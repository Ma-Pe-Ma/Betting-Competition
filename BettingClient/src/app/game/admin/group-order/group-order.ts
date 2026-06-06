import { Component } from '@angular/core';
import { CdkDrag, CdkDragDrop, CdkDropList, moveItemInArray} from '@angular/cdk/drag-drop';
import { HttpClient, HttpErrorResponse} from '@angular/common/http';
import { NgbAlertModule } from '@ng-bootstrap/ng-bootstrap';
import { finalize } from 'rxjs';
import { paths } from '../../../paths';

@Component({
  selector: 'app-group-order',
  imports: [CdkDropList, CdkDrag, NgbAlertModule],
  templateUrl: './group-order.html'
})
export class GroupOrder {
  groups: Group[] = [];
  alerts: Alert[] = []

  disabled = false;

  constructor(private http: HttpClient) {
    let getGroupPath = paths.admin.group.get;

    this.http.get<Group[]>(getGroupPath)
      .subscribe({
        next: (groups: Group[]) => {
          this.groups = groups;
        },
        error: (err: HttpErrorResponse) => {
          this.alerts.push({type: 'danger', message: err.error});
        }
      });
  }

  postGroupOrder() {
    this.disabled = true;
    let setGroupPath = paths.admin.group.set;

    this.http.post(setGroupPath, this.groups, {responseType: 'text'})
      .pipe(finalize(() => {this.disabled = false;}))
      .subscribe({
        next: (message: string) => {
          this.alerts.push({'type': 'success', 'message': message}); 
        },
        error: (err: HttpErrorResponse) => {
          this.alerts.push({'type': 'danger', 'message': err.error}); 
        }
      });
  }

  drop(event: CdkDragDrop<string[]>, teams: Team[]) {
    moveItemInArray(teams, event.previousIndex, event.currentIndex);
  }

  close(alert: Alert) {
		this.alerts.splice(this.alerts.indexOf(alert), 1);
	}
}
