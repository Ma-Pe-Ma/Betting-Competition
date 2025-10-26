import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PlayerResults } from './player-results';

describe('PlayerResults', () => {
  let component: PlayerResults;
  let fixture: ComponentFixture<PlayerResults>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PlayerResults]
    })
    .compileComponents();

    fixture = TestBed.createComponent(PlayerResults);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
