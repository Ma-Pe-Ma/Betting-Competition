import { Component } from '@angular/core';
import { environment } from '../../../../environments/environment';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { tap, catchError, of} from 'rxjs';
import { NgbAlertModule } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'app-maintenance',
  imports: [NgbAlertModule],
  templateUrl: './maintenance.html'
})
export class Maintenance {
  scheduledTasks: string[] = []
  serverAddress: string = environment.serverAddress;
  alerts: Alert[] = []

  selectedFile: File | null = null;
  
  constructor(private http: HttpClient) {

  }

  onFileSelected(event: any) {
    this.selectedFile = event.target.files[0];
  }

  uploadDB() {
    if (!this.selectedFile) {
      this.alerts.push({message: 'No file selected!', type: 'danger'} as Alert); 
      return;
    } 

    const formData = new FormData();
    formData.append('file', this.selectedFile);

    let path = environment.serverAddress + environment.locations.admin.maintenance.dbUpload;

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

  launchRequest(path: string) {
    let fullpath = environment.serverAddress + path;
    this.http.get<Alert>(fullpath).pipe(
      tap(data => {
        return data;  
      }),
      catchError((err: HttpErrorResponse) => {
        console.error('Error maintenance request:', err);
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
