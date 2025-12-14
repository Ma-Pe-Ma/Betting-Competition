import { Component } from '@angular/core';
import { environment } from '../../../../environments/environment';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { tap, catchError, of} from 'rxjs';
import { NgbAlertModule } from '@ng-bootstrap/ng-bootstrap';
import { ClientConfigService } from '../../../service/client-config-service';

@Component({
  selector: 'app-maintenance',
  imports: [NgbAlertModule],
  templateUrl: './maintenance.html'
})
export class Maintenance {
  scheduledTasks: string[] = []
  serverAddress: string;
  alerts: Alert[] = []

  selectedFile: File | null = null;
  
  constructor(private http: HttpClient, private clientConfigService: ClientConfigService) {
    this.serverAddress = this.clientConfigService.clientConfig.endpoint;
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

    let path = environment.locations.admin.maintenance.dbUpload;

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
    this.http.get<Alert>(path).pipe(
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
