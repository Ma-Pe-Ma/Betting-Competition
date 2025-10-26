import { Injectable } from '@angular/core';
import { BehaviorSubject, catchError, EMPTY, Observable, tap} from 'rxjs';
import { environment } from '../../environments/environment';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private userSubject = new BehaviorSubject<User | null>(null);

  constructor(private http: HttpClient) {
    
  }

  ngOnInit(): void {
    this.fetchAuthStatus();
  }

  private fetchAuthStatus() {
    let statusPath = environment.serverAddress + environment.locations.auth.status;

    this.http.get<User>(statusPath, {observe: 'response'}).pipe(
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
    ).subscribe();  
  }

  get getUser$(): Observable<User | null> {
    if (this.userSubject.value === null) {
      this.fetchAuthStatus();
    }

    return this.userSubject.asObservable();
  }

  signIn() {
    this.fetchAuthStatus();
  }

  signOut() {
    this.fetchAuthStatus();
  }
}
