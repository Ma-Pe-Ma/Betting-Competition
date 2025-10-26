import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SignOut } from './sign-out';

describe('SignOut', () => {
  let component: SignOut;
  let fixture: ComponentFixture<SignOut>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SignOut]
    })
    .compileComponents();

    fixture = TestBed.createComponent(SignOut);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
