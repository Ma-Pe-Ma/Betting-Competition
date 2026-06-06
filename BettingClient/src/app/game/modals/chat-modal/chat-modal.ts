import { Component, ViewChild, ElementRef, Output } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { MarkdownComponent, provideMarkdown } from 'ngx-markdown';
import { FormsModule } from '@angular/forms';
import { EventEmitter } from '@angular/core';
import { NgbAlertModule } from '@ng-bootstrap/ng-bootstrap';
import { finalize } from 'rxjs';
import { paths } from '../../../paths';

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

  disabled = false;

  constructor(private http: HttpClient, public activeModal: NgbActiveModal) {}

  ngAfterViewInit(): void {
    setTimeout(() => {
      this.commentInput.nativeElement.focus();
    });
  }

  createPreview() {
    this.previewText = this.inputMessage.comment ?? "";
  }

  postMessage() {
    this.disabled = true;
    let postChatPath = paths.chat.set;

    this.http.post(postChatPath, this.inputMessage, {responseType: 'text'})
      .pipe(finalize(() => {this.disabled = false;}))
      .subscribe({
        next: (message: string) => {
          this.postedMessage.emit(true);
          this.alerts.push({type: 'success', message: message});

          setTimeout(() => {
            this.activeModal.close();
          }, 1500);
        },
        error: (err: HttpErrorResponse) => {
          this.alerts.push({type: 'success', message: err.error});
        }
      });
  }

  close(alert: Alert) {
		this.alerts.splice(this.alerts.indexOf(alert), 1);
	}
}
