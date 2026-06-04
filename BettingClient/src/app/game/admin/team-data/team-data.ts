import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Component } from '@angular/core';
import { NgbAlertModule } from '@ng-bootstrap/ng-bootstrap';
import { tap, catchError, of } from 'rxjs';
import { paths } from '../../../paths';

@Component({
  selector: 'app-team-data',
  imports: [NgbAlertModule],
  templateUrl: './team-data.html'
})
export class TeamData {
  fileMap = new Map<string, File | null>([
    ['team', null],
    ['translation', null]
  ]);

  alerts: Alert[] = []

  constructor(private http: HttpClient) {

  }

  onFileSelected(fileId: string, event: any) {
    this.fileMap.set(fileId, event.target.files[0]);
  }

  uploadFiles() {
    if (!this.fileMap.get('team')) {
      this.alerts.push({message: $localize`@@noTeam: No team file selected!`, type: 'danger'} as Alert); 
      return;
    } 

    if (!this.fileMap.get('translation')) {
      this.alerts.push({message: $localize`@@noTranslation: No translation file selected!`, type: 'danger'} as Alert); 
      return;
    } 

    const formData = new FormData();
    formData.append('team', this.fileMap.get('team')!);
    formData.append('translation', this.fileMap.get('translation')!);

    let path = paths.admin.teamData;
    this.http.post<Alert>(path, formData)
    .subscribe({
      next: alert => this.alerts.push(alert),
      error: err => {
        console.error('Error uploading db:', err);
        this.alerts.push({
          message: $localize`:@@uploadError:Unknown error: ` + err.error,
          type: 'danger'
        });
      }
    });
  }
  
  close(alert: Alert) {
    this.alerts.splice(this.alerts.indexOf(alert), 1);
  }
}
