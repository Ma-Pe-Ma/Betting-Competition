import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ChatModal } from './chat-modal';

describe('ChatModal', () => {
  let component: ChatModal;
  let fixture: ComponentFixture<ChatModal>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ChatModal]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ChatModal);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
