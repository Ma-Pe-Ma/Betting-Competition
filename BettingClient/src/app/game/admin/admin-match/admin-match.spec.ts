import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AdminMatch } from './admin-match';

describe('AdminMatch', () => {
  let component: AdminMatch;
  let fixture: ComponentFixture<AdminMatch>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AdminMatch]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AdminMatch);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
