import { ComponentFixture, TestBed } from '@angular/core/testing';

import { GroupBefore } from './group-before';

describe('GroupBefore', () => {
  let component: GroupBefore;
  let fixture: ComponentFixture<GroupBefore>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GroupBefore]
    })
    .compileComponents();

    fixture = TestBed.createComponent(GroupBefore);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
