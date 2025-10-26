import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SendMessage } from './send-message';

describe('SendMessage', () => {
  let component: SendMessage;
  let fixture: ComponentFixture<SendMessage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SendMessage]
    })
    .compileComponents();

    fixture = TestBed.createComponent(SendMessage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
