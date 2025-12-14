import { Component, ViewChild, ElementRef, Output, input } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { MarkdownComponent, provideMarkdown } from 'ngx-markdown';
import { FormsModule } from '@angular/forms';
import { tap, catchError } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { EventEmitter } from '@angular/core';
import { NgbAlertModule } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'app-chat-modal',
  imports: [MarkdownComponent, FormsModule, NgbAlertModule],
  templateUrl: './chat-modal.html',
  providers: [provideMarkdown()]
})
export class ChatModal {
  @ViewChild('commentInput') commentInput!: ElementRef;
  @Output() postedMessage: EventEmitter<boolean> = new EventEmitter<boolean>();

  alerts: Alert[] = []

  inputMessage: ChatMessage = {}
  previewText: string = "";

  constructor(private http: HttpClient, public activeModal: NgbActiveModal) {
  
  }

  ngAfterViewInit(): void {
    setTimeout(() => {
      this.commentInput.nativeElement.focus();
    });
  }

  createPreview() {
    this.previewText = this.inputMessage.comment ?? "";
  }

  postMessage() {
    let postChatPath = environment.locations.chat.set;

    this.http.post<Alert>(postChatPath, this.inputMessage).pipe(
        tap(alert => {
          this.alerts.push(alert);          
          this.postedMessage.emit(true);

          if (alert.type == 'success') {
            setTimeout(() => {
              this.activeModal.close();
            }, 2000);            
          }          
        }),
        catchError(err => {
          console.error('Error fetching group results:', err);
          return [];
        })
      ).subscribe();
  }

  close(alert: Alert) {
		this.alerts.splice(this.alerts.indexOf(alert), 1);
	}
}
