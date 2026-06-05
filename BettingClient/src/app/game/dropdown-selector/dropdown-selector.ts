import { Component, Input, Output, EventEmitter } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { NgbDropdownModule } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'app-dropdown-selector',
  imports: [NgbDropdownModule],
  templateUrl: './dropdown-selector.html',
  standalone: true
})
export class DropdownSelector {
  @Input() selectorName: string = "";
  @Input() listLocation: string = "";
  @Input() defaultValue: string | null = null;
  @Output() itemSelected: EventEmitter<string> = new EventEmitter<string>();

  listElements: string[] = []
  selectedItem: string | null = null;

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.http.get<string[]>(this.listLocation)
      .subscribe({
        next: (listelements: string[]) => {
          this.listElements = listelements;

          if (this.defaultValue != null) { 
            this.onItemSelected(this.defaultValue);
          }
          else {
            this.onItemSelected(this.listElements[0]);
          }
        },
        error: (err: HttpErrorResponse) => {
          console.error('Error fetching dropdown list', err.error);
        }
      });  
  }

  onItemSelected(itemName: string) {
    this.selectedItem = itemName;
    this.itemSelected.emit(itemName);
  }
}
