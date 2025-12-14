import { Component } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { NgbAlertModule } from '@ng-bootstrap/ng-bootstrap';
import { environment } from '../../../environments/environment';
import { map, tap, catchError } from 'rxjs';
import { MarkdownComponent, provideMarkdown } from 'ngx-markdown';
import { ChatModal } from '../modals/chat-modal/chat-modal';
import { LocalDatePipe } from '../../pipes/local-date-pipe';
import { AuthService } from '../../service/auth-service';

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
    let groupStatusPath = environment.locations.chat.get;
    
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

    this.http.get<ChatMessage[]>(groupStatusPath, {params}).pipe(
      map(comments => ({
        comments,
        params
      })),  
      tap(data => {
        if (age == '>') {
          this.chatMessages.push(...data.comments);

          window.scrollTo({
            top: document.body.scrollHeight,
            behavior: 'smooth'
          });
        }
        else if (age == '<') {
          data.comments.reverse();
          this.chatMessages.unshift(...data.comments);

          window.scrollTo({
            top: 0,
            behavior: 'smooth'
          });

          this.previousDisabled = data.comments.length < 8 ? true : false;
        }
        
      }),
      catchError(err => {
        console.error('Error fetching group results:', err);
        return [];
      })
    ).subscribe();
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
