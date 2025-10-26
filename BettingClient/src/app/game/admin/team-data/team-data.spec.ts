import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TeamData } from './team-data';

describe('TeamData', () => {
  let component: TeamData;
  let fixture: ComponentFixture<TeamData>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TeamData]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TeamData);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
