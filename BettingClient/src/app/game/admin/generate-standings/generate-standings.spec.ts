import { ComponentFixture, TestBed } from '@angular/core/testing';

import { GenerateStandings } from './generate-standings';

describe('GenerateStandings', () => {
  let component: GenerateStandings;
  let fixture: ComponentFixture<GenerateStandings>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GenerateStandings]
    })
    .compileComponents();

    fixture = TestBed.createComponent(GenerateStandings);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
