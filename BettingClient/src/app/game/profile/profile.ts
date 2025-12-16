import { Component } from '@angular/core';
import { UserEditor } from '../../authentication/user-editor/user-editor';
import { Reminder } from '../../authentication/reminder/reminder';
import { HttpClient } from '@angular/common/http';
import { NgbAlert } from '@ng-bootstrap/ng-bootstrap';
import { paths } from '../../paths';

@Component({
  selector: 'app-profile',
  imports: [UserEditor, Reminder, NgbAlert],
  templateUrl: './profile.html'
})
export class Profile {
  userData: UserData = {}
  alerts: Alert[] = []

  constructor(private http: HttpClient) {
    let profilePath = paths.auth.profile.get;
    http.get<UserData>(profilePath).subscribe( profileData => {
      this.userData = profileData;
    });
  }

  postProfile() {
    let profilePath = paths.auth.profile.set;

    this.http.post<Alert>(profilePath, this.userData).subscribe(alert => {
        this.alerts.push(alert);
    });
  }

  close(alert: Alert) {
		this.alerts.splice(this.alerts.indexOf(alert), 1);
	}
}
