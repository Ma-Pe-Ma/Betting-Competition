import { Injectable } from '@angular/core';
import { BehaviorSubject, catchError, EMPTY, Observable, tap} from 'rxjs';
import { HttpClient, HttpParams } from '@angular/common/http';
import { paths } from '../paths';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private userSubject = new BehaviorSubject<User | null>(null);

  constructor(private http: HttpClient) {}

  public fetchAuthStatus(): Observable<any> {
    let statusPath = paths.auth.status;

    let params = new HttpParams()
      .set('lan', environment.languageKey);

    return this.http.get<User>(statusPath, {params: params, observe: 'response'}).pipe(
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
    return this.fetchAuthStatus();
  }

  signOut() {
    return this.fetchAuthStatus();
  }
}
