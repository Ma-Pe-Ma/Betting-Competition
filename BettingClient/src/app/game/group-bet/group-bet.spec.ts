import { ComponentFixture, TestBed } from '@angular/core/testing';

import { GroupBet } from './group-bet';

describe('GroupBet', () => {
  let component: GroupBet;
  let fixture: ComponentFixture<GroupBet>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GroupBet]
    })
    .compileComponents();

    fixture = TestBed.createComponent(GroupBet);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
