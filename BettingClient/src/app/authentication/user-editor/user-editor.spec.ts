import { ComponentFixture, TestBed } from '@angular/core/testing';

import { UserEditor } from './user-editor';

describe('UserEditor', () => {
  let component: UserEditor;
  let fixture: ComponentFixture<UserEditor>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [UserEditor]
    })
    .compileComponents();

    fixture = TestBed.createComponent(UserEditor);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
