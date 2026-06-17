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
  @Input() specialElements: [string, string][] = [];
  @Output() itemSelected: EventEmitter<string> = new EventEmitter<string>();
  
  listElements: [string, string][] = []
  selectedItem: [string, string] | null = null;

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.http.get<string[]>(this.listLocation)
      .subscribe({
        next: (listelements: string[]) => {
          this.listElements = [...this.specialElements, ...listelements.map(e => [e, e] as [string, string])];

          if (this.defaultValue != null) { 
            let defaultItem = this.listElements.find(e=>e[1] === this.defaultValue);

            if (defaultItem) {
              this.onItemSelected(defaultItem)
            }
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

  onItemSelected(item: [string, string]) {
    this.selectedItem = item;
    this.itemSelected.emit(item[1]);
  }
}
