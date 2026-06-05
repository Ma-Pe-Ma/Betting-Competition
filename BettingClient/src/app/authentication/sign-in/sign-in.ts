import { Component, ViewChild, ElementRef } from '@angular/core';
import { RouterModule, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { NgbAlertModule } from '@ng-bootstrap/ng-bootstrap';
import { AuthService } from '../../service/auth-service';
import { paths } from '../../paths';

@Component({
  selector: 'app-sign-in',
  imports: [RouterModule, FormsModule, NgbAlertModule],
  templateUrl: './sign-in.html'
})
export class SignIn {
  @ViewChild('userInput') userInput!: ElementRef;

  userData: UserData = {keepSignedIn: true}
  
  alerts: Alert[] = []

  ngAfterViewInit(): void {
    setTimeout(() => {
      this.userInput.nativeElement.focus();
    });
  }

  constructor(private router: Router, private http: HttpClient, private authService: AuthService) {}

  signIn() {
    let location = paths.auth.signIn;
    this.http.post(location, this.userData, {responseType: 'text'})
      .subscribe({
        next: (message: string)=> {
          this.alerts.push({type: 'success', message: message});

          this.authService.fetchAuthStatus().subscribe({
            next: () => {
              setTimeout(() => {
                this.router.navigate(['/']);
              }, 1000);
            }
          });    
          },
        error: (err: HttpErrorResponse) => {
          this.alerts.push({type: 'danger', message: err.error});
        }
      });
  }

  close(alert: Alert) {
		this.alerts.splice(this.alerts.indexOf(alert), 1);
	}
}
