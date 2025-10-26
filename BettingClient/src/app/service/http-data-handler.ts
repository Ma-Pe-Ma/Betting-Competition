import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse} from '@angular/common/http';
import { tap, catchError, Observable, of} from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class HttpDataHandler {
  constructor(private http: HttpClient) {
    
  }

  getData<T>(path: string): Observable<T|Alert> {
    return this.http.get<T>(path).pipe(
      tap(data => {
        return data;
      }),
      catchError((err: HttpErrorResponse) => {
        if (err.status == 400) {
          return of(err.error as Alert);
        }
        
        console.error('Error updating matches:', err);
        return of({message: 'Unknown error: ' + err.error, type: 'danger'} as Alert);
      })
    );
  }

  postData<T>(path: string, data: T): Observable<Alert> {
    return this.http.post<Alert>(path, data).pipe(
      tap(data => {
        return data;
      }),
      catchError((err: HttpErrorResponse) => {
        console.error('Error updating matches:', err);
        return of({message: 'Unknown error: ' +err.error, type: 'danger'} as Alert);
      })
    );
  }
}
