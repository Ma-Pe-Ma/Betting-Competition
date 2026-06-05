import { Component } from '@angular/core';
import { paths } from '../../../paths';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';

interface ResetKey {
  email: string
  date: string
  key: string
}

@Component({
  selector: 'app-password-reset',
  imports: [],
  templateUrl: './password-reset.html'
})
export class PasswordReset {
  resetKeys: ResetKey[] = []

  constructor(private http: HttpClient) {
    let resetKeyPath = paths.admin.resetKeys;
    
    this.http.get<ResetKey[]>(resetKeyPath)
      .subscribe({
        next: (value: ResetKey[]) => {
          this.resetKeys = value as ResetKey[];
        },
        error: (err: HttpErrorResponse) => {
          //this.alerts.push({type: 'danger', message: err.error});
        }
    });
  }
}


