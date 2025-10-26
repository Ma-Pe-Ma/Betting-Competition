import { ComponentFixture, TestBed } from '@angular/core/testing';

import { HomeMessage } from './home-message';

describe('HomeMessage', () => {
  let component: HomeMessage;
  let fixture: ComponentFixture<HomeMessage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HomeMessage]
    })
    .compileComponents();

    fixture = TestBed.createComponent(HomeMessage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
