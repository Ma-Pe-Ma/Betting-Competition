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

    return this.http.get<User>(statusPath, {params: params}).pipe(
      tap({
        next: (user: User) => {
          this.userSubject.next(user);
        },
        error: () => {
          this.userSubject.next(null);
        }
      })
    )
  }

  getUser(): User {
    return this.userSubject.value!;
  }

  get getUser$(): Observable<User | null> {
    return this.userSubject.asObservable();
  }

  updateUserField(updatedFields: Partial<User>) {
    const currentUser = this.userSubject.value;

    if (currentUser) {
      this.userSubject.next({
        ...currentUser,
        ...updatedFields
      });
    }
}
}
