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
  teamFile: File | null = null;
  translationFile: File | null = null;
  alerts: Alert[] = []

  constructor(private http: HttpClient) {

  }

  onFileSelected(file: File|null, event: any) {
    file = event.target.files[0];
  }

  uploadFiles() {
    if (!this.teamFile) {
      this.alerts.push({message: 'No team file selected!', type: 'danger'} as Alert); 
      return;
    } 

    if (!this.translationFile) {
      this.alerts.push({message: 'No translation file selected!', type: 'danger'} as Alert); 
      return;
    } 

    const formData = new FormData();
    formData.append('team', this.teamFile);
    formData.append('translation', this.translationFile);

    let path = paths.admin.teamData;
    this.http.post<Alert>(path, formData).pipe(
      tap(data => {
        return data;  
      }),
      catchError((err: HttpErrorResponse) => {
        console.error('Error uploading db:', err);
        return of({message: 'Unknown error: ' + err.error, type: 'danger'} as Alert);
      })
    )
    .subscribe(value => {
      this.alerts.push(value as Alert);      
    });
  }
  
  close(alert: Alert) {
    this.alerts.splice(this.alerts.indexOf(alert), 1);
  }
}
