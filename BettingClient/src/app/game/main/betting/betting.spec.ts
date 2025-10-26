import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Betting } from './betting';

describe('Betting', () => {
  let component: Betting;
  let fixture: ComponentFixture<Betting>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Betting]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Betting);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
