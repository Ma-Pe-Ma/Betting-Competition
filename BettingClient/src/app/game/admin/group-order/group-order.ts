import { Component } from '@angular/core';
import { CdkDrag, CdkDragDrop, CdkDropList, moveItemInArray} from '@angular/cdk/drag-drop';
import { HttpClient} from '@angular/common/http';
import { environment } from '../../../../environments/environment';
import { NgbAlertModule } from '@ng-bootstrap/ng-bootstrap';
import { HttpDataHandler } from '../../../service/http-data-handler';

@Component({
  selector: 'app-group-order',
  imports: [CdkDropList, CdkDrag, NgbAlertModule],
  templateUrl: './group-order.html'
})
export class GroupOrder {
  groups: Group[] = [];
  alerts: Alert[] = []

  constructor(private http: HttpClient, private httpDataHandler: HttpDataHandler) {
    let getGroupPath = environment.locations.admin.group.get;

    this.httpDataHandler.getData<Group[]>(getGroupPath).subscribe(value => {
      if (value && (value as any).message) {
        this.alerts.push(value as Alert);
      }
      else {
        this.groups = value as Group[];
      }
    });
  }

  postGroupOrder() {
    let setGroupPath = environment.locations.admin.group.set;

    this.httpDataHandler.postData(setGroupPath, this.groups).subscribe(value => {
        this.alerts.push(value); 
    });
  }

  drop(event: CdkDragDrop<string[]>, teams: Team[]) {
    moveItemInArray(teams, event.previousIndex, event.currentIndex);
  }

  close(alert: Alert) {
		this.alerts.splice(this.alerts.indexOf(alert), 1);
	}
}
