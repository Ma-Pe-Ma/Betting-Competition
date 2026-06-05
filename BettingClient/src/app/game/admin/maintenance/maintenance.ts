import { Component } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { NgbAlertModule } from '@ng-bootstrap/ng-bootstrap';
import { ClientConfigService } from '../../../service/client-config-service';
import { paths } from '../../../paths';

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

    let path = paths.admin.maintenance.dbUpload;

    this.http.post(path, formData, {responseType: 'text'})
      .subscribe({
        next: (message: string)=> {
          this.alerts.push({type: 'success', message: message});      
        },
        error: (err: HttpErrorResponse) => {
          this.alerts.push({type: 'danger', message: err.error});
        }      
      });
  }

  launchRequest(path: string) {
    this.http.get(path, {responseType: 'text'})
      .subscribe({
        next: (message: string)=> {
          this.alerts.push({type: 'success', message: message});
        },
        error: (err: HttpErrorResponse) => {
          //console.error('Error maintenance request:', err);
          this.alerts.push({type: 'danger', message: err.error});
        }
      });
  }

  close(alert: Alert) {
    this.alerts.splice(this.alerts.indexOf(alert), 1);
  }
}
