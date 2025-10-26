import { ComponentFixture, TestBed } from '@angular/core/testing';

import { GroupAfter } from './group-after';

describe('GroupAfter', () => {
  let component: GroupAfter;
  let fixture: ComponentFixture<GroupAfter>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GroupAfter]
    })
    .compileComponents();

    fixture = TestBed.createComponent(GroupAfter);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
