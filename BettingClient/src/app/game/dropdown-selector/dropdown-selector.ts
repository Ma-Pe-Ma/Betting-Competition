import { Component, Input, Output, EventEmitter } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, tap, catchError, EMPTY } from 'rxjs';
import { NgbDropdownModule } from '@ng-bootstrap/ng-bootstrap';
import { AsyncPipe } from '@angular/common';
import { AuthService } from '../../service/auth-service';

@Component({
  selector: 'app-dropdown-selector',
  imports: [NgbDropdownModule, AsyncPipe],
  templateUrl: './dropdown-selector.html',
  standalone: true
})
export class DropdownSelector {
  @Input() selectorName: string = "";
  @Input() listLocation: string = "";
  @Input() defaultValue: string | null = null;
  @Output() itemSelected: EventEmitter<string> = new EventEmitter<string>();

  listElements$: BehaviorSubject<string[] | null> = new BehaviorSubject<string[] | null>(null);
  selectedItem: string | null = null;

  constructor(private http: HttpClient, private authService: AuthService) {
    
  }

  ngOnInit() {
    this.http.get<string[]>(this.listLocation, {observe: 'response'}).pipe(
      tap(res => {
        
        if (res.status === 200) {
          this.listElements$.next(res.body);

          if (this.defaultValue != null) { 
            this.onItemSelected(this.defaultValue);
          }
          else {
            this.onItemSelected(this.listElements$.value![0]);
          }
        }
        else {
          this.listElements$.next(null);
        }
      }),
      catchError(err => {
        console.error('Error fetching dropdown list', err);
        return EMPTY;
      })
    ).subscribe();  
  }

  onItemSelected(itemName: string) {
    this.selectedItem = itemName;
    this.itemSelected.emit(itemName);
  }
}
