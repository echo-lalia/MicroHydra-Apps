"""Simple little boids sim."""
from lib.display.fancydisplay import FancyDisplay as Display
from .vector2d import Vector2D as Vec
from lib.userinput import UserInput
from lib.hydra import color
from machine import freq
from array import array
import random


freq(240_000_000)

DISPLAY = Display()
USER_INPUT = UserInput()
_DISPLAY_LEN_PX = max(DISPLAY.width, DISPLAY.height)



class Boid:
    """The little boids."""

    shape = array('h', (0,0, 6,2, 0,4, 2,2))

    def __init__(self, position, velocity, clr):
        """Create a single boid."""
        self.pos = position
        self.v = velocity
        self.clr = clr
        self.r = 0.0
        # Useful to store values later:
        self.dist = 0.0
        self.mag = 0.0

    def steer(self, boids, processed_boids):
        """See all neighbors, and apply velocity."""
        avoiding_boids = [self]
        following_boids = [self]

        # sort boids into categories of avoiding (too close) and following (within safe distance)
        for boid in boids:
            if boid not in processed_boids:
                dist = self.pos.distance(boid.pos)
                if dist < Simulation.avoid_radius:
                    boid.dist = dist
                    avoiding_boids.append(boid)
                if dist < Simulation.follow_radius:
                    following_boids.append(boid)

        # Avoid too close boids
        if len(avoiding_boids) > 1:
            avoid_center = Vec.mean(boid.pos for boid in avoiding_boids)
            for boid in avoiding_boids:
                dist = boid.dist
                # dont divide by zero:
                if dist != 0.0:
                    # normalize avoid vector based on boid distance (if we dont do this,
                    # closer boids will avoid less than far boids)
                    avoid_vec = (boid.pos - avoid_center) * (Simulation.avoid_radius / dist)
                    boid.v += avoid_vec * Simulation.avoid_weight * (Simulation.avoid_radius - dist)

        # follow other boids
        if len(following_boids) > 1:
            follow_center = Vec.mean(boid.pos for boid in following_boids)
            avg_v = Vec.mean(boid.v for boid in following_boids)
            for boid in following_boids:
                boid.v += (follow_center - boid.pos)*Simulation.follow_weight + avg_v*Simulation.avg_v_weight

    def dampen(self):
        """Apply min/max speed."""
        self.mag = self.v.magnitude()
        if self.mag > Simulation.max_speed:
            self.v = self.v * (Simulation.max_speed / self.mag)
        elif self.mag < Simulation.min_speed and self.mag != 0.0:
            self.v = self.v * (Simulation.min_speed / self.mag)

    def move(self, max_x, max_y):
        """Move the boid."""
        self.pos += self.v
        if (not 0 <= self.pos.x <= max_x) \
        or (not 0 <= self.pos.y <= max_y):
            self.pos %= Vec(max_x, max_y)

        self.r = self.v.phase()

    def draw(self, display):
        """Draw the boid."""
        display.polygon(
            self.shape,
            int(self.pos.x),
            int(self.pos.y),
            self.clr,
            angle=self.r,
        )


class Obstical:
    """An obstical for the boids."""

    min_v = 0.01
    max_v = 0.5

    def __init__(self):
        """Construct a random obstical."""
        self.visual_radius = random.randint(_DISPLAY_LEN_PX//50, _DISPLAY_LEN_PX//15)
        self.radius = self.visual_radius + 6
        self.avoid_radius = Simulation.ob_avoid_radius
        self.avoid_weight = Simulation.ob_avoid_weight
        self.avoid_dist = self.radius + self.avoid_radius

        self.min_x = self.visual_radius + _DISPLAY_LEN_PX/20
        self.max_x = DISPLAY.width - self.min_x
        self.min_y = self.min_x
        self.max_y = DISPLAY.height - self.min_x

        self.pos = Vec(
            random.uniform(self.min_x, self.max_x),
            random.uniform(self.min_y, self.max_y),
        )
        self.v = Vec(
            random.uniform(self.min_v, self.max_v),
            random.uniform(self.min_v, self.max_v),
        )
        self.clr, self.bump_clr = self._rand_color()
        self.bumped = False

    @staticmethod
    def _rand_color() -> int:
        r,g,b = color.hsv_to_rgb(
            random.random(),
            random.uniform(0.5, 0.9),
            1.0,
        )
        r = int(r*31)
        g = int(g*63)
        b = int(b*31)
        return color.combine_color565(r//2,g//2,b//2), color.combine_color565(r,g,b)

    def move(self):
        """Move the obstical."""
        self.pos += self.v
        # If out of bounds
        if (not self.min_x <= self.pos.x <= self.max_x) \
        or (not self.min_y <= self.pos.y <= self.max_y):
            # flip x and/or y velocity
            if (not self.min_x <= self.pos.x <= self.max_x):
                self.v = Vec(-self.v.x, self.v.y)
            if (not self.min_y <= self.pos.y <= self.max_y):
                self.v = Vec(self.v.x, -self.v.y)
            # clamp position
            x = max(min(self.pos.x, self.max_x), self.min_x)
            y = max(min(self.pos.y, self.max_y), self.min_y)
            self.pos = Vec(x, y)

    def draw(self, display):
        """Draw the obstical."""
        display.ellipse(
            int(self.pos.x), int(self.pos.y),
            self.visual_radius, self.visual_radius,
            self.bump_clr if self.bumped else self.clr,
        )
        self.bumped = False

    def affect(self, boids):
        """Affect all the boids."""
        for boid in boids:
            dist = self.pos.distance(boid.pos)
            if dist < self.avoid_dist and dist != 0.0:
                # multiply by avoid weight, and scale so closer object avoid faster
                avoid_vec = (boid.pos - self.pos) / dist
                # hard collision if inside of the obstical
                if dist < self.radius:
                    self.bumped = True
                    boid.pos = self.pos + avoid_vec * self.radius
                    # Bounce back
                    boid.v += boid.mag * avoid_vec
                    avoid_vec = avoid_vec * Simulation.avoid_weight
                else:
                    avoid_vec = avoid_vec * self.avoid_weight * (self.avoid_radius - (dist - self.radius))

                boid.v += avoid_vec




class Simulation:
    """The manager of the boid sim."""

    num_boids = 0
    follow_per_frame = 0

    num_obs = 0
    ob_avoid_radius = 0.0
    ob_avoid_weight = 0.0

    avoid_radius = 0.0
    avoid_weight = 0.0

    follow_radius = 0.0
    follow_weight = 0.0

    avg_v_weight = 0.0
    min_speed = 0.0
    max_speed = 0.0

    def __init__(self, display, _input):
        """Create a simulation."""
        Simulation._choose_sim()

        self.display = display
        self.input = _input
        self.boids = [self._rand_boid() for _ in range(Simulation.num_boids)]

        self.affected_idx = 0
        self.processed_boids = set()

        self.obs = [Obstical() for _ in range(Simulation.num_obs)]

    @classmethod
    def _choose_sim(cls):
        # Select a random (pre-defined) scenario
        (
        cls.num_boids,
        cls.follow_per_frame,

        cls.num_obs,
        cls.ob_avoid_radius,
        cls.ob_avoid_weight,

        cls.avoid_radius,
        cls.avoid_weight,

        cls.follow_radius,
        cls.follow_weight,

        cls.avg_v_weight,
        cls.min_speed,
        cls.max_speed,
        ) = random.choice((
            (# Orderly
                # Num boids, per frame,
                13, 4,
                # num obs, ob avoid radius, weight
                1 + (_DISPLAY_LEN_PX//300), 80, 0.01,
                # Avoid radius, weight,
                _DISPLAY_LEN_PX/16, 0.02,
                # Follow radius, weight,
                _DISPLAY_LEN_PX * 0.4, 0.02,
                # avg v weight, min, max,
                0.2, 1.0, 4.0,
            ),
            (# Bumpers
                # Num boids, per frame,
                11, 5,
                # num obs, ob avoid radius, weight
                2, 5, 0.001,
                # Avoid radius, weight,
                10.0, 0.5,
                # Follow radius, weight,
                _DISPLAY_LEN_PX / 4, 0.02,
                # avg v weight, min, max,
                0.01, 2.0, 6.0,
            ),
            (# Fish
                # Num boids, per frame,
                30, 2,
                # num obs, ob avoid radius, weight
                1 + (_DISPLAY_LEN_PX//300), 20, 0.1,
                # Avoid radius, weight,
                _DISPLAY_LEN_PX*0.0625, 0.01,
                # Follow radius, weight,
                _DISPLAY_LEN_PX / 3, 0.01,
                # avg v weight, min, max,
                0.3, 2.5, 3.0,
            ),
            (# Birds
                # Num boids, per frame,
                17, 2,
                # num obs, ob avoid radius, weight
                1 + (_DISPLAY_LEN_PX//300), _DISPLAY_LEN_PX*(60/320) + 10, 0.07,
                # Avoid radius, weight,
                _DISPLAY_LEN_PX*(50/320), 0.001,
                # Follow radius, weight,
                _DISPLAY_LEN_PX/3, 0.05,
                # avg v weight, min, max,
                0.2, 5.0, 8.5,
            ),
            (# OBSTICALS
                # Num boids, per frame,
                11, 5,
                # num obs, ob avoid radius, weight
                _DISPLAY_LEN_PX//40, 30, 0.1,
                # Avoid radius, weight,
                _DISPLAY_LEN_PX*(20/320), 0.05,
                # Follow radius, weight,
                _DISPLAY_LEN_PX / 4, 0.08,
                # avg v weight, min, max,
                0.6, 2.0, 6.0,
            ),
            (# SPEEDY
                # Num boids, per frame,
                6, 4,
                # num obs, ob avoid radius, weight
                _DISPLAY_LEN_PX//90, _DISPLAY_LEN_PX*0.2, 0.1,
                # Avoid radius, weight,
                _DISPLAY_LEN_PX*0.08, 0.05,
                # Follow radius, weight,
                _DISPLAY_LEN_PX*0.4, 0.15,
                # avg v weight, min, max,
                0.6, 6.0, 8.0,
            ),
        ))

        # Adjust weights based on frame amount (makes the value more consistent)
        Simulation.avoid_weight /= Simulation.follow_per_frame
        Simulation.follow_weight /= Simulation.follow_per_frame
        Simulation.avg_v_weight /= Simulation.follow_per_frame



    @staticmethod
    def _rand_color() -> int:
        r,g,b = color.hsv_to_rgb(
            random.random(),
            random.uniform(0.5, 1.0),
            1.0,
        )
        r = int(r*31)
        g = int(g*63)
        b = int(b*31)
        return color.combine_color565(r,g,b)


    def _rand_boid(self) -> Boid:
        return Boid(
            Vec(random.uniform(0, self.display.width),
                random.uniform(0, self.display.height)),
            Vec(random.uniform(-0.1, 0.1),
                random.uniform(-0.1, 0.1)),
            self._rand_color(),
        )

    def step(self):
        """Do one simulation step."""
        # move all boids towards average position and velocity
        boids = self.boids

        max_x = self.display.width
        max_y = self.display.height

        # Move the obsticals!
        for ob in self.obs:
            ob.move()
            ob.affect(boids)


        for _ in range(Simulation.follow_per_frame):
            # To save CPU cycles, pick ONE boid at a time.
            # This boid will be affected by all other boids, and all other boids will be affected by it.
            # No other relationships will be calculated this cycle
            self.affected_idx = (self.affected_idx + 1) % len(boids)
            one_boid = boids[self.affected_idx]

            self.processed_boids.add(one_boid)
            one_boid.steer(boids, self.processed_boids)
        self.processed_boids.clear()

        # Apply the average velocity to all boids
        for boid in boids:
            boid.dampen()
            boid.move(max_x, max_y)

    def main(self):
        """Run the simulation."""
        while True:

            if "ENT" in self.input.get_new_keys():
                return

            self.display.fill(0)
            self.step()
            for boid in self.boids:
                boid.draw(self.display)
            for ob in self.obs:
                ob.draw(self.display)

            self.display.show()


# Sim exits on Enter. (Create a new sim!)
while True:
    sim = Simulation(DISPLAY, USER_INPUT)
    sim.main()
