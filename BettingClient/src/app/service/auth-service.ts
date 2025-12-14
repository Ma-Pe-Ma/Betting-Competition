import { Injectable } from '@angular/core';
import { BehaviorSubject, catchError, EMPTY, Observable, tap} from 'rxjs';
import { environment } from '../../environments/environment';
import { HttpClient } from '@angular/common/http';
import { getDefaultFormatCodeSettings } from 'typescript';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private userSubject = new BehaviorSubject<User | null>(null);

  constructor(private http: HttpClient) {}

  public fetchAuthStatus(): Observable<any> {
    let statusPath = environment.locations.auth.status;

    return this.http.get<User>(statusPath, {observe: 'response'}).pipe(
      tap(res => {
        if (res.status === 200) {
          this.userSubject.next(res.body);
        }
        else {
          this.userSubject.next(null);
        }
      }),
      catchError(err => {
        console.error('Error fetching auth status', err);
        return EMPTY
      })
    )
  }

  getUser(): User {
    return this.userSubject.value!;
  }

  get getUser$(): Observable<User | null> {
    return this.userSubject.asObservable();
  }

  signIn() {
    this.fetchAuthStatus().subscribe();
  }

  signOut() {
    this.fetchAuthStatus().subscribe();
  }
}
