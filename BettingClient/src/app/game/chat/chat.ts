import { Component } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { NgbAlertModule } from '@ng-bootstrap/ng-bootstrap';
import { MarkdownComponent, provideMarkdown } from 'ngx-markdown';
import { ChatModal } from '../modals/chat-modal/chat-modal';
import { LocalDatePipe } from '../../pipes/local-date-pipe';
import { AuthService } from '../../service/auth-service';
import { paths } from '../../paths';

@Component({
  selector: 'app-chat',
  imports: [NgbAlertModule, MarkdownComponent, LocalDatePipe],
  templateUrl: './chat.html',
  providers: [provideMarkdown()]
})
export class Chat {
  alerts: Alert[] = []
  chatMessages: ChatMessage[] = []

  previousDisabled: boolean = true;
  user: User;

  constructor(private http: HttpClient, private modalService: NgbModal, private authService: AuthService) {
    this.getComments()
    this.user = this.authService.getUser();
  }

  getComments(age: string|null = '<') {
    let groupStatusPath = paths.chat.get;
    
    let dateString: string|undefined;

    if (this.chatMessages.length > 0) {
      if (age === '>') {
        dateString = this.chatMessages[this.chatMessages.length - 1].datetime;
      }
      else if (age === '<') {
        dateString = this.chatMessages[0].datetime;
      }
    }    

    let params = new HttpParams();
    if (dateString) params = params.set('datetime', dateString);
    if (age !== null) params = params.set('age', age);

    this.http.get<ChatMessage[]>(groupStatusPath, {params})
      .subscribe({
        next: (chatMessages: ChatMessage[]) => {
          if (age == '>') {
            this.chatMessages.push(...chatMessages);

            window.scrollTo({
              top: document.body.scrollHeight,
              behavior: 'smooth'
            });
          }
          else if (age == '<') {
            chatMessages.reverse();
            this.chatMessages.unshift(...chatMessages);

            window.scrollTo({
              top: 0,
              behavior: 'smooth'
            });

            this.previousDisabled = chatMessages.length < 8 ? true : false;
          }
        },
        error: (err: HttpErrorResponse) => {
          this.alerts.push({type: 'danger', message: err.error})
        }
      });
  }

  showNewCommentModal() {
    const modalRef = this.modalService.open(ChatModal);
    let chatModal: ChatModal = modalRef.componentInstance;

    chatModal.postedMessage.subscribe((posted: boolean) => {
      if (this.chatMessages.length > 0) {
        this.getComments('>');
      }
    })    
  }

  close(alert: Alert) {
		this.alerts.splice(this.alerts.indexOf(alert), 1);
	}
}
