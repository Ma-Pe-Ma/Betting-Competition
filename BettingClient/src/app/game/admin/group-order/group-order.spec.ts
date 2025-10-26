import { ComponentFixture, TestBed } from '@angular/core/testing';

import { GroupOrder } from './group-order';

describe('GroupOrder', () => {
  let component: GroupOrder;
  let fixture: ComponentFixture<GroupOrder>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GroupOrder]
    })
    .compileComponents();

    fixture = TestBed.createComponent(GroupOrder);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
