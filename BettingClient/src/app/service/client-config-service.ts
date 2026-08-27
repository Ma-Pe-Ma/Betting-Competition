import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { tap, Observable } from 'rxjs';

interface ClientConfig {
  endpoint: string;
}

@Injectable({
  providedIn: 'root'
})
export class ClientConfigService {
  constructor(private http: HttpClient) {}

  config!: ClientConfig;

  loadConfig(): Observable<any> {
    return this.http.get<ClientConfig>('./config.json').pipe(
      tap(data => {
        this.config = data;
      })
    );
  }

  get clientConfig(): ClientConfig {
    return this.config;
  }
}
